class TokenSaver < Formula
  desc "Zero-cost, zero-latency token optimization engine and intelligent MCP middleware"
  homepage "https://github.com/Farukes/Token-Saver"
  version "1.0.0"
  license "BUSL-1.1"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.0/token-saver-darwin-arm64.tar.gz"
      sha256 "0f3f1afaaf0a614e4f7d2f220d5a6bc2f38242d586dd95b423578a83639e0199"
    else
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.0/token-saver-darwin-x64.tar.gz"
      sha256 "3b2f0f66f7754d5e9971df7b52668bdf844b972cdc90b228db9b39bec2e76c5b"
    end
  end

  on_linux do
    url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.0/token-saver-linux-x64.tar.gz"
    sha256 "1421afa91cffcb4422e56a1597924f95cdec0e6b909c1d79edd5f5da157eb266"
  end

  def install
    bin.install "token-saver"
  end

  test do
    assert_match "token-saver", shell_output("#{bin}/token-saver --help")
  end
end
