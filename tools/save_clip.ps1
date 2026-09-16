param([string]$Path)
Start-Sleep -Seconds 3
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$img = [System.Windows.Forms.Clipboard]::GetImage()
if ($img) { $img.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png); "saved $($img.Width)x$($img.Height)" } else { "no image" }
