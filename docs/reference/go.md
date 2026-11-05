# Go: a function and its example test

Put the function in `greet.go`:

```go
package greeting

import "strings"

func Greet(name string) string {
    name = strings.TrimSpace(name)
    if name == "" {
        return "Hello"
    }
    return "Hello, " + name
}
```

Put this executable documentation in `example_test.go`:

```go
package greeting

import "fmt"

func ExampleGreet() {
    fmt.Println(Greet("Ada"))
    // Output: Hello, Ada
}
```

`go test` checks the output comment. With a local module and cached dependencies,
`GOTOOLCHAIN=local GOPROXY=off go test ./...` requires no downloads.

**DOCS → GO PACKAGES** accepts `fmt.Printf`, `io.Reader` or `net/http` and displays
`go doc` output in the terminal. **GO EXAMPLES** opens the installed package's
example test files. Those files show complete call sequences and expected output.
The documentation helper disables toolchain and module downloads.
