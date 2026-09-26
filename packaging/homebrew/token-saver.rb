class TokenSaver < Formula
  desc "Zero-cost, zero-latency token optimization engine and intelligent MCP middleware"
  homepage "https://github.com/Farukes/Token-Saver"
  version "1.0.1"
  license "BUSL-1.1"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-darwin-arm64.tar.gz"
      sha256 "01c5d96664be27704feb197619cdf47297dc4a9a6e9e941ddd0bc4a2a372bc07"
    else
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-darwin-x64.tar.gz"
      sha256 "74557a58d0a815cdaf828c3a46f2617280ba045aca6bdcb4f3160fb908dff845"
    end
  end

  on_linux do
    url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-linux-x64.tar.gz"
    sha256 "2b7c48a70fe0bb998e7928302c1d3eb9803226f62b597a34cc228d93edda6729"
  end

  def install
    bin.install "token-saver"
  end

  test do
    assert_match "token-saver", shell_output("#{bin}/token-saver --help")
  end
end
