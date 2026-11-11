# Command-line and network tools

Selected from [The Book of Secret Knowledge](https://github.com/trimstray/the-book-of-secret-knowledge) by trimstray, commit `7d37069a361d`, under the MIT license in [LICENSE.md](LICENSE.md).

## CLI Tools

### Files and directories

- [fd](https://github.com/sharkdp/fd) - is a simple, fast and user-friendly alternative to find.
- [ncdu](https://dev.yorhel.nl/ncdu) - is an easy to use, fast disk usage analyzer.

### Network

- [PuTTY](https://www.putty.org/) - is an SSH and telnet client, developed originally by Simon Tatham.
- [Mosh](https://mosh.org/) - is a SSH wrapper designed to keep a SSH session alive over a volatile connection.
- [Eternal Terminal](https://eternalterminal.dev/) - enables mouse-scrolling and tmux commands inside the SSH session.
- [nmap](https://nmap.org/) - is a free and open source (license) utility for network discovery and security auditing.
- [zmap](https://github.com/zmap/zmap) - is a fast single packet network scanner designed for Internet-wide network surveys.
- [Rust Scan](https://github.com/RustScan/RustScan) - to find all open ports faster than Nmap.
- [masscan](https://github.com/robertdavidgraham/masscan) - is the fastest Internet port scanner, spews SYN packets asynchronously.
- [pbscan](https://github.com/gvb84/pbscan) - is a faster and more efficient stateless SYN scanner and banner grabber.
- [hping](http://www.hping.org/) - is a command-line oriented TCP/IP packet assembler/analyzer.
- [mtr](https://github.com/traviscross/mtr) - is a tool that combines the functionality of the 'traceroute' and 'ping' programs in a single tool.
- [mylg](https://github.com/mehrdadrad/mylg) - utility which combines the functions of the different network probes in one diagnostic tool.
- [netcat](http://netcat.sourceforge.net/) - utility which reads and writes data across network connections, using the TCP/IP protocol.
- [socat](http://www.dest-unreach.org/socat/) - utility which transfers data between two objects.
- [tcpdump](https://www.tcpdump.org/) - is a powerful command-line packet analyzer.
- [tshark](https://www.wireshark.org/docs/man-pages/tshark.html) - is a tool that allows us to dump and analyze network traffic (wireshark cli).
- [Termshark](https://termshark.io/) - is a simple terminal user-interface for tshark.
- [ngrep](https://github.com/jpr5/ngrep) - is like GNU grep applied to the network layer.
- [netsniff-ng](http://netsniff-ng.org/) - is a Swiss army knife for your daily Linux network plumbing if you will.
- [sockdump](https://github.com/mechpen/sockdump) - dump unix domain socket traffic.
- [stenographer](https://github.com/google/stenographer) - is a packet capture solution which aims to quickly spool all packets to disk.
- [tcpterm](https://github.com/sachaos/tcpterm) - visualize packets in TUI.
- [bmon](https://github.com/tgraf/bmon) - is a monitoring and debugging tool to capture networking related statistics and prepare them visually.
- [iptraf-ng](http://iptraf.seul.org/2.6/manual.html#installation) - is a console-based network monitoring program for Linux that displays information about IP traffic.
- [vnstat](https://github.com/vergoh/vnstat) - is a network traffic monitor for Linux and BSD.
- [iPerf3](https://iperf.fr/) - is a tool for active measurements of the maximum achievable bandwidth on IP networks.
- [ethr](https://github.com/Microsoft/Ethr) - is a Network Performance Measurement Tool for TCP, UDP & HTTP.
- [Etherate](https://github.com/jwbensley/Etherate) - is a Linux CLI based Ethernet and MPLS traffic testing tool.
- [echoip](https://github.com/mpolden/echoip) - is a IP address lookup service.
- [Nemesis](https://github.com/troglobit/nemesis) - packet manipulation CLI tool; craft and inject packets of several protocols.
- [packetfu](https://github.com/packetfu/packetfu) - a mid-level packet manipulation library for Ruby.
- [Scapy](https://scapy.net/) - packet manipulation library; forge, send, decode, capture packets of a wide number of protocols.
- [impacket](https://github.com/SecureAuthCorp/impacket) - is a collection of Python classes for working with network protocols.
- [ssh-audit](https://github.com/arthepsy/ssh-audit) - is a tool for SSH server auditing.
- [aria2](https://aria2.github.io/) - is a lightweight multi-protocol & multi-source command-line download utility.
- [iptables-tracer](https://github.com/x-way/iptables-tracer) - observe the path of packets through the iptables chains.
- [inception](https://github.com/proabiral/inception) - a highly configurable tool to check for whatever you like against any number of hosts.
- [mRemoteNG](https://mremoteng.org/) - a fork of mRemote, multi-tabbed PuTTy on steroids!

### Network (DNS)

- [dnsdiag](https://github.com/farrokhi/dnsdiag) - is a DNS diagnostics and performance measurement tools.
- [fierce](https://github.com/mschwager/fierce) - is a DNS reconnaissance tool for locating non-contiguous IP space.
- [subfinder](https://github.com/subfinder/subfinder) - is a subdomain discovery tool that discovers valid subdomains for websites.
- [sublist3r](https://github.com/aboul3la/Sublist3r) - is a fast subdomains enumeration tool for penetration testers.
- [amass](https://github.com/OWASP/Amass) - is tool that obtains subdomain names by scraping data sources, crawling web archives, and more.
- [namebench](https://github.com/google/namebench) - provides personalized DNS server recommendations based on your browsing history.
- [massdns](https://github.com/blechschmidt/massdns) - is a high-performance DNS stub resolver for bulk lookups and reconnaissance.
- [knock](https://github.com/guelfoweb/knock) - is a tool to enumerate subdomains on a target domain through a wordlist.
- [dnsperf](https://github.com/DNS-OARC/dnsperf) - DNS performance testing tools.
- [dnscrypt-proxy 2](https://github.com/jedisct1/dnscrypt-proxy) - a flexible DNS proxy, with support for encrypted DNS protocols.
- [dnsdbq](https://github.com/dnsdb/dnsdbq) - API client providing access to passive DNS database systems.
- [grimd](https://github.com/looterz/grimd) - fast dns proxy, built to black-hole internet advertisements and malware servers.
- [dnstwist](https://github.com/elceef/dnstwist) - detect typosquatters, phishing attacks, fraud, and brand impersonation.

### Network (HTTP)

- [curl](https://curl.haxx.se/) - is a command line tool and library for transferring data with URLs.
- [kurly](https://gitlab.com/davidjpeacock/kurly) - is an alternative to the widely popular curl program, written in Golang.
- [HTTPie](https://github.com/jakubroztocil/httpie) - is an user-friendly HTTP client.
- [wuzz](https://github.com/asciimoo/wuzz) - is an interactive cli tool for HTTP inspection.
- [h2spec](https://github.com/summerwind/h2spec) - is a conformance testing tool for HTTP/2 implementation.
- [h2t](https://github.com/gildasio/h2t) - is a simple tool to help sysadmins to hardening their websites.
- [htrace.sh](https://github.com/trimstray/htrace.sh) - is a simple Swiss Army knife for http/https troubleshooting and profiling.
- [httpstat](https://github.com/reorx/httpstat) - is a tool that visualizes curl statistics in a way of beauty and clarity.
- [httplab](https://github.com/gchaincl/httplab) - is an interactive web server.
- [Lynx](https://lynx.browser.org/) - is a text browser for the World Wide Web.
- [Browsh](https://github.com/browsh-org/browsh/) - is a fully interactive, real-time, and modern text-based browser.
- [HeadlessBrowsers](https://github.com/dhamaniasad/HeadlessBrowsers) - a list of (almost) all headless web browsers in existence.
- [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) - is a single-threaded command line tool for measuring the performance of HTTP web servers.
- [siege](https://www.joedog.org/siege-home/) - is an http load testing and benchmarking utility.
- [wrk](https://github.com/wg/wrk) - is a modern HTTP benchmarking tool capable of generating significant load.
- [wrk2](https://github.com/giltene/wrk2) - is a constant throughput, correct latency recording variant of wrk.
- [vegeta](https://github.com/tsenart/vegeta) - is a constant throughput, correct latency recording variant of wrk.
- [bombardier](https://github.com/codesenberg/bombardier) - is a fast cross-platform HTTP benchmarking tool written in Go.
- [gobench](https://github.com/cmpxchg16/gobench) - http/https load testing and benchmarking tool.
- [hey](https://github.com/rakyll/hey) - HTTP load generator, ApacheBench (ab) replacement, formerly known as rakyll/boom.
- [boom](https://github.com/tarekziade/boom) - is a script you can use to quickly smoke-test your web app deployment.
- [SlowHTTPTest](https://github.com/shekyan/slowhttptest) - is a tool that simulates some Application Layer Denial of Service attacks by prolonging HTTP.
- [gobuster](https://github.com/OJ/gobuster) - is a free and open source directory/file & DNS busting tool written in Go.
- [ssllabs-scan](https://github.com/ssllabs/ssllabs-scan) - command-line reference-implementation client for SSL Labs APIs.
- [http-observatory](https://github.com/mozilla/http-observatory) - Mozilla HTTP Observatory cli version.
- [Hurl](https://hurl.dev) - is a command line tool to run and test HTTP requests with plain text.

### SSL

- [openssl](https://www.openssl.org/) - is a robust, commercial-grade, and full-featured toolkit for the TLS and SSL protocols.
- [gnutls-cli](https://gnutls.org/manual/html_node/gnutls_002dcli-Invocation.html) - client program to set up a TLS connection to some other computer.
- [sslyze](https://github.com/nabla-c0d3/sslyze) - fast and powerful SSL/TLS server scanning library.
- [sslscan](https://github.com/rbsec/sslscan) - tests SSL/TLS enabled services to discover supported cipher suites.
- [testssl.sh](https://github.com/drwetter/testssl.sh) - testing TLS/SSL encryption anywhere on any port.
- [cipherscan](https://github.com/mozilla/cipherscan) - a very simple way to find out which SSL ciphersuites are supported by a target.
- [spiped](http://www.tarsnap.com/spiped.html) - is a utility for creating symmetrically encrypted and authenticated pipes between socket addresses.
- [Certbot](https://github.com/certbot/certbot) - is EFF's tool to obtain certs from Let's Encrypt and (optionally) auto-enable HTTPS on your server.
- [mkcert](https://github.com/FiloSottile/mkcert) - simple zero-config tool to make locally trusted development certificates with any names you'd like.
- [certstrap](https://github.com/square/certstrap) - tools to bootstrap CAs, certificate requests, and signed certificates.
- [Sublert](https://github.com/yassineaboukir/sublert) - is a security and reconnaissance tool to automatically monitor new subdomains.
- [mkchain](https://github.com/trimstray/mkchain) - open source tool to help you build a valid SSL certificate chain.
- [ssl-cert-check](https://github.com/Matty9191/ssl-cert-check) - SSL Certification Expiration Checker.

### System Diagnostics/Debuggers

- [strace](https://github.com/strace/strace) - diagnostic, debugging and instructional userspace utility for Linux.
- [DTrace](http://dtrace.org/blogs/about/) - is a performance analysis and troubleshooting tool.
- [ltrace](https://en.wikipedia.org/wiki/Ltrace) - is a library call tracer, used to trace calls made by programs to library functions.
- [ptrace-burrito](https://github.com/brainsmoke/ptrace-burrito) - is a friendly wrapper around ptrace.
- [perf-tools](https://github.com/brendangregg/perf-tools) - performance analysis tools based on Linux perf\_events (aka perf) and ftrace.
- [bpftrace](https://github.com/iovisor/bpftrace) - high-level tracing language for Linux eBPF.
- [sysdig](https://github.com/draios/sysdig) - system exploration and troubleshooting tool with first class support for containers.
- [Valgrind](http://www.valgrind.org/) - is an instrumentation framework for building dynamic analysis tools.
- [gperftools](https://github.com/gperftools/gperftools) - high-performance multi-threaded malloc() implementation, plus some performance analysis tools.
- [glances](https://nicolargo.github.io/glances/) - cross-platform system monitoring tool written in Python.
- [htop](https://github.com/hishamhm/htop) - interactive text-mode process viewer for Unix systems. It aims to be a better 'top'.
- [bashtop](https://github.com/aristocratos/bashtop) - Linux resource monitor written in pure Bash.
- [nmon](http://nmon.sourceforge.net/pmwiki.php) - a single executable for performance monitoring and data analysis.
- [atop](https://www.atoptool.nl/) - ASCII performance monitor. Includes statistics for CPU, memory, disk, swap, network, and processes.
- [lsof](https://en.wikipedia.org/wiki/Lsof) - displays in its output information about files that are opened by processes.
- [FlameGraph](http://www.brendangregg.com/flamegraphs.html) - stack trace visualizer.
- [lsofgraph](https://github.com/zevv/lsofgraph) - convert Unix lsof output to a graph showing FIFO and UNIX interprocess communication.
- [rr](https://github.com/mozilla/rr) - is a lightweight tool for recording, replaying and debugging execution of applications.
- [Performance Co-Pilot](https://pcp.io/index.html) - a system performance analysis toolkit.
- [hexyl](https://github.com/sharkdp/hexyl) - a command-line hex viewer.
- [Austin](https://github.com/p403n1x87/austin) - Python frame stack sampler for CPython.

### Log Analyzers

- [angle-grinder](https://github.com/rcoh/angle-grinder) - slice and dice log files on the command line.
- [lnav](https://lnav.org) - log file navigator with search and automatic refresh.
- [GoAccess](https://goaccess.io/) - real-time web log analyzer and interactive viewer that runs in a terminal.
- [ngxtop](https://github.com/lebinh/ngxtop) - real-time metrics for nginx server.

### Databases

- [usql](https://github.com/xo/usql) - universal command-line interface for SQL databases.
- [pgcli](https://github.com/dbcli/pgcli) - postgres CLI with autocompletion and syntax highlighting.
- [mycli](https://github.com/dbcli/mycli) - terminal client for MySQL with autocompletion and syntax highlighting.
- [litecli](https://github.com/dbcli/litecli) - SQLite CLI with autocompletion and syntax highlighting.
- [mssql-cli](https://github.com/dbcli/mssql-cli) - SQL Server CLI with autocompletion and syntax highlighting.
- [OSQuery](https://github.com/osquery/osquery) - is a SQL powered operating system instrumentation, monitoring, and analytics framework.
- [pgsync](https://github.com/ankane/pgsync) - sync data from one Postgres database to another.
- [iredis](https://github.com/laixintao/iredis) - a terminal client for redis with autocompletion and syntax highlighting.
- [SchemaCrawler](https://www.schemacrawler.com/diagramming.html) - generates an E-R diagram of your database.

## Networks

### Tools

- [CapAnalysis](https://www.capanalysis.net/ca/) - web visual tool to analyze large amounts of captured network traffic (PCAP analyzer).
- [netbox](https://github.com/digitalocean/netbox) - IP address management (IPAM) and data center infrastructure management (DCIM) tool.

### Labs

- [NRE Labs](https://labs.networkreliability.engineering/) - learn automation by doing it. Right now, right here, in your browser.

### Other

- [LBNL's Network Research Group](https://ee.lbl.gov/) - home page of the Network Research Group (NRG).
