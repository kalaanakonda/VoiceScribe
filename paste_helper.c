/*
 * paste_helper — sends Cmd+V via CGEventPost.
 *
 * Lives inside VoiceScribe.app/Contents/MacOS/ so that TCC attributes the
 * keystroke to VoiceScribe (com.voicescribe.app) instead of to Python.
 * Python calls this binary as a subprocess after copying text to the
 * clipboard.
 *
 * Build:  clang -arch arm64 -O2 -framework ApplicationServices \
 *           -o paste_helper paste_helper.c
 */
#include <ApplicationServices/ApplicationServices.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    /* tiny delay so the focused app has time to receive focus */
    usleep(80000);

    CGEventSourceRef src = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState);

    /* keyDown: V (kVK_ANSI_V = 9) with Command flag */
    CGEventRef down = CGEventCreateKeyboardEvent(src, (CGKeyCode)9, true);
    CGEventSetFlags(down, kCGEventFlagMaskCommand);
    CGEventPost(kCGHIDEventTap, down);
    CFRelease(down);

    /* keyUp */
    CGEventRef up = CGEventCreateKeyboardEvent(src, (CGKeyCode)9, false);
    CGEventSetFlags(up, kCGEventFlagMaskCommand);
    CGEventPost(kCGHIDEventTap, up);
    CFRelease(up);

    if (src) CFRelease(src);
    return 0;
}
