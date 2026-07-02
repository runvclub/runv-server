import net from 'node:net';
import tls from 'node:tls';
import { readFileSync } from 'node:fs';
import { fileTypeStream } from 'file-type';

const port = process.env.PORT || 1965;
const host = '0.0.0.0';

const options = {
  key: readFileSync(new URL('./certs/nexy.localhost.key', import.meta.url)),
  cert: readFileSync(new URL('./certs/nexy.localhost.pem', import.meta.url))
};

const MAX_URL = 2048;

const server = tls.createServer(options, async (socket) => {
  socket.once('error', (err) => console.error(err));

  let url;
  try {
    url = await readUrl(socket);
    if (url.protocol !== 'nex:') {
      return socket.end(`50 Unsupported scheme`);
    }
  } catch (err) {
    return socket.end(`59 ${err.message}\r\n`);
  }

  try {
    const client = await fetchResource(url);
    const stream = await fileTypeStream(client);
    const mimetype = (stream.fileType && stream.fileType.mime) || 'text/gemini';
    const status = 20;
    socket.write(`${status} ${mimetype}\r\n`);
    stream.pipe(socket);
  } catch (err) {
    const status = 43;
    return socket.end(`${status} ${err.message}\r\n`);
  }
});
server.listen(port, host, () => {
  console.log(`Server listening on ${host}:${port}`);
});

function fetchResource(url) {
  const { host, pathname: selector } = url;
  const port = parseInt(url.port, 10) || 1900;
  return new Promise((resolve, reject) => {
    const client = net.createConnection(port, host, () => {
      client.write(`${selector}\n`);
      resolve(client);
    });
    client.once('error', reject);
  });
}

function readUrl(socket) {
  return new Promise((resolve, reject) => {
    socket.once('readable', () => {
      try {
        socket.setEncoding('utf-8');
        const url = socket.read(MAX_URL) || socket.read();
        resolve(new URL(url));
      } catch (err) {
        reject(err);
      }
    });
  });
}
