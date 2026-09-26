class TokenSaver < Formula
  desc "Zero-cost, zero-latency token optimization engine and intelligent MCP middleware"
  homepage "https://github.com/Farukes/Token-Saver"
  version "1.0.1"
  license "BUSL-1.1"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-darwin-arm64.tar.gz"
      sha256 "9003d12f616077ccd13ff5b649dea347fcdaa287de74b617d1fbbd4da53e1618"
    else
      url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-darwin-x64.tar.gz"
      sha256 "d2149e96002442eeb35b95260259c392a478eef0646fe1cec3e527f1feebd980"
    end
  end

  on_linux do
    url "https://github.com/Farukes/Token-Saver/releases/download/v1.0.1/token-saver-linux-x64.tar.gz"
    sha256 "83c7f71f1edb7c55fe493c657041eec90247fc2a9ff2bfb2cc0bcd4f7d01d6ad"
  end

  def install
    bin.install "token-saver"
  end

  test do
    assert_match "token-saver", shell_output("#{bin}/token-saver --help")
  end
end
