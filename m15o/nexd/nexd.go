package main

import (
	"bufio"
	"hg.sr.ht/~m15o/nex-pfm"
	"io"
	"log"
	"net"
	"os"
)

func serve(h *nex.Handler, rw io.ReadWriteCloser) {
	defer rw.Close()
	scanner := bufio.NewScanner(rw)
	scanner.Scan()
	sel := scanner.Text()
	if err := h.Handle(sel, rw); err != nil {
		rw.Write([]byte("document not found"))
		log.Println(err)
	}
}

func listenAndServe(h *nex.Handler) error {
	l, err := net.Listen("tcp", ":1900")
	if err != nil {
		return err
	}
	defer l.Close()

	for {
		rw, err := l.Accept()
		if err != nil {
			return err
		}
		go serve(h, rw)
	}
}

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: nexd path")
	}

	h := nex.Handler{FS: os.DirFS(os.Args[1])}
	log.Fatal(listenAndServe(&h))
}
