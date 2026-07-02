unit mainunit;

{$mode objfpc}{$H+}

interface

uses
  Classes, SysUtils, Forms, Controls, Graphics, Dialogs, StdCtrls,
  ExtCtrls, ActnList, Buttons, IpHtml, ssockets, URIParser, strutils;

const
  Scheme = 'nex';
  Port = 1900;
  ByteBufferSize = 1024 * 64;

type

  TURL = record
    scheme, host, selector: string;
  end;

  TLink = record
    Name, url: string;
  end;

  THistory = class
    index: integer;
    history: TStringList;
    function Back(): string;
    function Next(): string;
    function CanNext(): boolean;
    function CanBack(): boolean;
    procedure Push(url: string);
    constructor Create;
    destructor Destroy; override;
  end;


  { TForm1 }

  TForm1 = class(TForm)
    Image1: TImage;
    Memo1: TMemo;
    GoBtn: TButton;
    Panel1: TPanel;
    BackBtn: TSpeedButton;
    NextBtn: TSpeedButton;
    UpBtn: TButton;
    URLEdit: TEdit;
    procedure BackBtnClick(Sender: TObject);
    procedure FormClose(Sender: TObject; var CloseAction: TCloseAction);
    procedure FormCreate(Sender: TObject);
    procedure GoBtnClick(Sender: TObject);
    procedure Memo1Click(Sender: TObject);
    procedure NextBtnClick(Sender: TObject);
    procedure UpBtnClick(Sender: TObject);
    procedure FormActivate(Sender: TObject);
    procedure URLEditKeyPress(Sender: TObject; var Key: char);
    procedure LoadImageFromString(const ImgData: TBytes);
    procedure Go();
  private
    URL: TURL;
    History: THistory;
    procedure Request(Addr: string; Port: integer; What: string;
      out stream: TMemoryStream);
    function SetURL: boolean;
  end;

var
  Form1: TForm1;

implementation

{$R *.lfm}

{ TForm1 }

constructor THistory.Create;
begin
  history := TStringList.Create;
end;

destructor THistory.Destroy;
begin
  history.Free;
  inherited;
end;

function StripScheme(const url: string): string;
begin
  Result := Copy(url, Pos('://', url) + 3, MaxInt);
end;

function GetHost(const url: string): string;
var
  p: integer;
  s: string;
begin
  s := url;
  p := Pos('/', s);
  if p = 0 then
    Result := s
  else
    Result := Copy(s, 1, p - 1);
end;

function GetSelector(const url: string): string;
var
  p: integer;
begin
  p := Pos('/', url);
  if p = 0 then
    Result := ''
  else
    Result := Copy(url, p, MaxInt);
end;

function TForm1.SetURL: boolean;
var
  p: integer;
  u: string;
begin
  // First we strip the scheme
  p := Pos(scheme + '://', URLEdit.Text);
  if p = 0 then
    Exit(False);
  u := Copy(URLEdit.Text, p + 6, MaxInt);

  // Then we get the host
  URL.host := GetHost(u);
  if Length(URL.host) = 0 then
    Exit(False);

  // Then we get the selector
  URL.selector := GetSelector(u);
  if Length(URL.selector) = 0 then
  begin
    URL.selector := '/';
    URLEdit.Text := URLEdit.Text + '/';
  end;
  Result := True;
end;

function ProcessLink(const line: string; const u: TURL; out link: TLink): boolean;
var
  resolvedUrl: string;
  pieces: TStringArray;
  Value: string;
  i: integer;
begin
  // First we split the string at spaces:
  pieces := SplitString(Trim(Copy(line, 3, MaxInt)), ' ');
  // When length < 1 we exit
  if Length(pieces) = 0 then
    Exit(False);

  if Length(pieces) = 1 then
    Value := pieces[0]
  else
  begin
    for i := 1 to High(pieces) do
    begin
      Value := Value + pieces[i];
      if i < High(pieces) then
        Value := Value + ' ';
    end;
  end;

  ResolveRelativeURI(scheme + '://' + u.host + u.selector,
    pieces[0], resolvedUrl);
  link.Name := Value;
  link.url := resolvedUrl;
end;

procedure StackPush(var s: TStringArray; e: string);
begin
  SetLength(s, Length(s) + 1);
  s[Length(s) - 1] := e;
end;

function FullURL(const u: TURL): string;
begin
  Result := scheme + '://' + u.host + u.selector;
end;

procedure TForm1.GoBtnClick(Sender: TObject);
begin
  history.push(URLEdit.Text);
  Go;
  BackBtn.Enabled := History.CanBack;
  NextBtn.Enabled := History.CanNext;
end;

function GetExtension(const u: string): string;
var
  p: integer;
begin
  p := LastDelimiter('.', u);
  if p = 0 then
    Result := ''
  else
    Result := Copy(u, p, MaxInt);
end;

procedure TForm1.LoadImageFromString(const ImgData: TBytes);
var
  MS: TMemoryStream;
begin
  MS := TMemoryStream.Create;
  try
    MS.WriteBuffer(Pointer(ImgData)^, Length(ImgData));
    MS.Position := 0;
    Image1.Picture.LoadFromStream(MS);
  finally
    MS.Free;
  end;
end;

procedure TForm1.Go;
var
  stream: TMemoryStream;
  Page: string;
  Lines: TStringList;
  i: integer;
  ext: string;
begin
  if SetURL = False then
  begin
    ShowMessage('Error processing the URL');
    Exit;
  end;

  stream := TMemoryStream.Create;
  Request(URL.host, Port, URL.Selector, stream);
  ext := GetExtension(URL.Selector);

  if (ext = '.jpeg') or (ext = '.jpg') or (ext = '.png') then
  begin
    Memo1.Visible := False;
    Image1.Visible := True;
    Image1.Picture.LoadFromStream(stream);
  end
  else
  begin
    Memo1.Visible := True;
    Image1.Visible := False;
    Lines := TStringList.Create;
    try
      Lines.LoadFromStream(stream);
      Lines.Text := LineEnding + Lines.Text;
      for i := 1 to Lines.Count - 1 do
        Lines[i] := '  ' + Lines[i];
      Page := Lines.Text;
    finally
      Lines.Free
    end;
    Memo1.Text := Page;
  end;

  FreeAndNil(stream);
end;

procedure TForm1.Memo1Click(Sender: TObject);
var
  link: TLink;
  line: string;
begin
  line := Copy(Memo1.Lines[Memo1.CaretPos.Y], 3, MaxInt);
  if Pos('=>', line) = 1 then
  begin
    ProcessLink(line, url, link);
    URLEdit.Text := link.url;
    GoBtn.Click;
  end;
end;

procedure TForm1.NextBtnClick(Sender: TObject);
begin
  URLEdit.Text := History.Next();
  BackBtn.Enabled := History.CanBack;
  NextBtn.Enabled := History.CanNext;
  Go;
end;

procedure TForm1.BackBtnClick(Sender: TObject);
begin
  URLEdit.Text := History.Back();
  BackBtn.Enabled := History.CanBack;
  NextBtn.Enabled := History.CanNext;
  Go;
end;

procedure TForm1.FormClose(Sender: TObject; var CloseAction: TCloseAction);
begin
  History.Free;
end;

procedure TForm1.FormCreate(Sender: TObject);
begin
  History := THistory.Create;
end;

procedure TForm1.UpBtnClick(Sender: TObject);
var
  p: integer;
begin
  if SetURL = False then
  begin
    ShowMessage('Error processing the URL');
    Exit;
  end;
  if URL.selector = '/' then
    Exit;
  p := LastDelimiter('/', URLEdit.Text);
  if p = Length(URLEdit.Text) then
  begin
    URLEdit.Text := Copy(URLEdit.Text, 1, p - 1);
    p := LastDelimiter('/', URLEdit.Text);
  end;
  if p <> 0 then
    URLEdit.Text := Copy(URLEdit.Text, 1, p);
  GoBtn.Click;
end;

procedure TForm1.FormActivate(Sender: TObject);
begin
  GoBtn.Click;
end;

procedure TForm1.URLEditKeyPress(Sender: TObject; var Key: char);
begin
  if Key = #13 then
    GoBtn.Click;
end;

procedure TForm1.Request(Addr: string; Port: integer; What: string;
  out stream: TMemoryStream);
var
  Conn: TInetSocket = nil;
  Buffer: array [1..ByteBufferSize] of byte;
  ReadBytes: integer;
begin
  try
    Conn := TInetSocket.Create(Addr, Port);
    What += #13#10;
    Conn.Write((@What[1])^, Length(What));
    while True do
    begin
      ReadBytes := Conn.Read(Buffer, ByteBufferSize);
      if ReadBytes < 1 then break;
      stream.WriteBuffer(buffer, ReadBytes);
    end;
  except
    MessageDlg('Failed to get data', 'Failed to get data: ' +
      Exception(ExceptObject).Message, mtError, [mbOK], 0);
  end;
  stream.Seek(0, soFromBeginning);
  FreeAndNil(Conn);
end;

function THistory.Back: string;
begin
  if index = 0 then
    Exit(history.Strings[0]);

  index := index - 1;
  Result := history.Strings[index];
end;

function THistory.CanNext: boolean;
begin
  Result := index <> (history.Count - 1);
end;

function THistory.CanBack(): boolean;
begin
  Result := index > 0;
end;

function THistory.Next(): string;
begin
  if index = history.Count - 1 then
    Exit(history.Strings[history.Count - 1]);

  index := index + 1;
  Result := history.Strings[index];
end;

procedure THistory.Push(url: string);
begin
  if history.Count <> 0 then
    while index <> history.Count - 1 do
      history.Delete(index + 1);
  history.Add(url);
  index := history.Count - 1;
end;


end.
