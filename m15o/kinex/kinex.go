package main

import (
	"bufio"
	"flag"
	"fmt"
	"hg.sr.ht/~m15o/nex-pfm"
	"html"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"
	"text/template"
)

var defaultTpl = `<!doctype html>
<html>
<head>
	<title>{{.title}}</title>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<style>{{.style}}</style>
    <link rel="stylesheet" href=".style.css">
</head>
<body>
	<div class="nex">{{.header}}</div>
	{{.content}}
</body>
`

func replaceLinks(input string) string {
	re := regexp.MustCompile(`(?m)^=&gt; (\S*)`)
	return re.ReplaceAllStringFunc(input, func(match string) string {
		url := re.FindStringSubmatch(match)[1]
		return fmt.Sprintf(`=> <a href="%s">%s</a>`, url, url)
	})
}

func breadcrumb(path string) string {
	if path == "/" {
		return ""
	}

	dir := ""
	if strings.HasSuffix(path, "/") {
		dir = "/"
	}

	parts := strings.Split(strings.Trim(path, "/"), "/")
	rv, parts := parts[len(parts)-1]+dir, parts[:len(parts)-1]
	for i := len(parts) - 1; i >= 0; i-- {
		rv = fmt.Sprintf("<a href=\"/%s/\">%s</a>/%s", strings.Join(parts[:i+1], "/"), parts[i], rv)
	}

	return rv
}

type server struct {
	style, host string
	t           *template.Template
	nex         nex.Handler
}

var re = regexp.MustCompile(`\S \n`)

func esc(s string) string {
	return html.EscapeString(s)
}

func xtwToHTML(x string) string {
	x = re.ReplaceAllString(x, " ")
	s := bufio.NewScanner(strings.NewReader(x))
	var rv string
	pre := false
	list := false
	for s.Scan() {
		l := s.Text()
		if pre && !strings.HasPrefix(l, "  ") {
			pre = false
			rv += "</pre>"
		}
		if list && !strings.HasPrefix(l, "* ") {
			list = false
			rv += "</ul>"
		}
		if strings.HasPrefix(l, "# ") {
			rv += "<h1>" + esc(l[2:]) + "</h1>"
		} else if strings.HasPrefix(l, "## ") {
			rv += "<h2>" + esc(l[3:]) + "</h2>"
		} else if strings.HasPrefix(l, "### ") {
			rv += "<h3>" + esc(l[4:]) + "</h3>"
		} else if strings.HasPrefix(l, "> ") {
			rv += "<blockquote>" + esc(l[2:]) + "</blockquote>"
		} else if strings.HasPrefix(l, "* ") {
			if !list {
				rv += "<ul>"
				list = true
			}
			rv += "<li>" + esc(l[2:]) + "</li>"
		} else if strings.HasPrefix(l, "  ") {
			if !pre {
				rv += "<pre>"
				pre = true
			} else {
				rv += "\n"
			}
			rv += esc(l[2:])
		} else if strings.TrimSpace(l) != "" {
			rv += "<p>" + esc(l) + "</p>"
		}
	}
	return rv
}

func (s *server) renderPath(w http.ResponseWriter, p string) error {
	var txt strings.Builder
	if err := s.nex.Handle(p, &txt); err != nil {
		return err
	}
	if strings.HasSuffix(p, "/") {
		return s.render(w, p, "<pre>"+replaceLinks(html.EscapeString(txt.String()))+"<pre>")
	}
	if strings.HasSuffix(p, ".txt") {
		return s.render(w, p, "<pre>"+html.EscapeString(txt.String())+"<pre>")
	}
	if strings.HasSuffix(p, ".xtw") {
		return s.render(w, p, "<div class=\"xtw\">"+xtwToHTML(txt.String())+"</div>")
	}
	if strings.HasSuffix(p, ".css") {
		w.Header().Set("Content-Type", "text/css")
	}
	_, err := w.Write([]byte(txt.String()))
	return err
}

func (s *server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	err := s.renderPath(w, r.URL.Path)
	if err != nil {
		http.Error(w, "Document not found", http.StatusNotFound)
		log.Println(err)
		return
	}
}

func (s *server) render(w io.Writer, path, content string) error {
	return s.t.Execute(w, map[string]string{
		"title":   path,
		"style":   s.style,
		"header":  fmt.Sprintf("echo %s | nc <a href=\"%s\">%s</a> 1900 | less", breadcrumb(path), "https://"+s.host, s.host),
		"content": content,
	})
}

func read(p, value string) ([]byte, error) {
	dat := []byte(value)
	var err error

	if p != "" {
		dat, err = os.ReadFile(p)
		if err != nil {
			return dat, err
		}
	}

	return dat, err
}

func main() {
	p := flag.String("p", "8080", "the port to listen on")
	s := flag.String("s", "", "the stylesheet to apply")
	t := flag.String("t", "", "template file to use")
	flag.Parse()

	if flag.NArg() < 2 {
		log.Fatal("usage: kinex dir host")
	}

	style, err := read(*s, "")
	if err != nil {
		log.Fatal(err)
	}

	tpl, err := read(*t, defaultTpl)
	if err != nil {
		log.Fatal(err)
	}

	h := server{
		nex:   nex.Handler{FS: os.DirFS(flag.Arg(0))},
		style: string(style),
		host:  flag.Arg(1),
		t:     template.Must(template.New("layout").Parse(string(tpl))),
	}

	http.Handle("/", &h)
	log.Fatal(http.ListenAndServe(":"+*p, nil))
}
