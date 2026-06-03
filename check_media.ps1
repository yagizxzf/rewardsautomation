# Check if any media is currently playing via Windows Media Transport Controls.
# Returns: PLAYING | NOT_PLAYING | NO_SESSION | ERROR

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime] | Out-Null
    [Windows.Foundation.IAsyncOperation`1,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null

    $AsyncOp = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()

    $TaskAwaiterType = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'GetAwaiter' -and
        $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    } | Select-Object -First 1

    $GenericMethod = $TaskAwaiterType.MakeGenericMethod([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
    $Awaiter = $GenericMethod.Invoke($null, @($AsyncOp))
    $Manager = $Awaiter.GetResult()

    $Session = $Manager.GetCurrentSession()
    if ($Session) {
        $PlaybackInfo = $Session.GetPlaybackInfo()
        $Status = $PlaybackInfo.PlaybackStatus
        # PlaybackStatus enum: 0=Closed, 1=Opened, 2=Changing, 3=Stopped, 4=Playing, 5=Paused
        if ($Status -eq 4) {
            Write-Output "PLAYING"
        } else {
            Write-Output "NOT_PLAYING"
        }
    } else {
        Write-Output "NO_SESSION"
    }
} catch {
    Write-Output "ERROR"
}
