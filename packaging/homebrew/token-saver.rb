class TokenSaver < Formula
  desc "Zero-cost, zero-latency token optimization engine and intelligent MCP middleware"
  homepage "https://github.com/Farukes/Token-Saver"
  version "1.0.1"
  license "BUSL-1.1"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-darwin-arm64.tar.gz"
      sha256 "9018a00efcaace0a32a8ebf95c313e0ed07ca6c6088ef38a3229c1bc06ab1801"
    else
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-darwin-x64.tar.gz"
      sha256 "ecfe4c28fc859ea0ceec3c3a64ef107bff08701be8999f96056188d715facc18"
    end
  end

  on_linux do
    url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-linux-x64.tar.gz"
    sha256 "4383e450623c1f01bf0ced3a27fa7344c7a7f0ec6694bac4ec09837014118e60"
  end

  def install
    bin.install "token-saver"
  end

  test do
    assert_match "token-saver", shell_output("#{bin}/token-saver --help")
  end
end
