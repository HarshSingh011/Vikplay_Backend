# WebRTC Live Streaming Test Guide

## 🚀 Step-by-Step Testing Instructions

### Prerequisites
1. Ensure FastAPI server is running on http://127.0.0.1:8000
2. Open the test page: http://127.0.0.1:8000/static/webrtc-test.html
3. Allow camera and microphone access when prompted

---

## 📹 Broadcasting (Creating a Live Stream)

### Step 1: Create a Stream
1. **Fill in Stream Details:**
   - Stream Title: `"My Test Stream"`
   - Description: `"Testing WebRTC broadcasting"`
   - Broadcaster ID: `"broadcaster_001"` (keep this consistent)
   - Video Quality: Select `720p HD` (recommended)

2. **Click "🚀 Create Stream"**
   - ✅ Should show: "Stream created successfully! Stream ID: X"
   - ✅ Note the Stream ID (e.g., 4)
   - ✅ "📡 Start Broadcasting" button should become enabled

### Step 2: Start Broadcasting
1. **Click "📡 Start Broadcasting"**
   - 🎥 Browser will request camera/microphone permission → **ALLOW**
   - ✅ Local video preview should appear
   - ✅ Should show "Local Preview - LIVE" with red pulsing indicator
   - ✅ Status should show "Broadcasting live!"
   - ✅ Check logs for: "Broadcasting WebRTC connection established!"

2. **Verify Stream is Live:**
   - Click "🔄 Refresh Stream List"
   - ✅ Your stream should show "🔴 LIVE" status
   - ✅ Status should say "Status: LIVE"

---

## 👁️ Viewing (Watching a Live Stream)

### Step 3: Watch the Stream
1. **In the Viewer Panel:**
   - Enter the Stream ID from Step 1 (e.g., 4)
   - Viewer Name: `"Viewer_001"`

2. **Click "▶️ Start Watching"**
   - ✅ Should show "Successfully connected to stream!"
   - ✅ Remote video should appear showing the broadcaster's video
   - ✅ Should show "Watching Stream X" overlay
   - ✅ Check logs for: "Viewer WebRTC connection established!"

---

## 🔍 Debugging & Troubleshooting

### Debug Commands
1. **Click "🐛 Debug Status"** to see:
   - Active broadcasters and their connection states
   - Current viewers
   - Client ID mappings

2. **Check System Logs** for:
   - ICE candidate exchanges
   - Connection state changes
   - Error messages

### Common Issues & Solutions

#### Issue: "Waiting for stream" / No video preview
**Solution:**
- Ensure camera/microphone permissions are granted
- Check browser console for errors
- Try refreshing the page and starting over

#### Issue: Stream shows "Offline" even when broadcasting
**Solution:**
- Click "🐛 Debug Status" to check if broadcaster is registered
- Verify the Stream ID matches between broadcaster and viewer
- Check server logs for WebRTC connection errors

#### Issue: Viewer can't connect to stream
**Solution:**
- Ensure broadcaster is actively streaming (red "LIVE" indicator)
- Use the exact Stream ID from the broadcaster
- Check that both use the same server (127.0.0.1:8000)

#### Issue: Connection drops or quality issues
**Solution:**
- Check network connectivity with "🔍 Test Connectivity"
- Try lower video quality (480p or 360p)
- Restart both broadcaster and viewer

---

## 🎯 Expected Behavior

### When Broadcasting Works:
1. Local video shows your camera feed
2. "LIVE" indicator pulses red
3. Stream list shows "🔴 LIVE" status
4. Statistics show bytes sent increasing
5. Debug status shows active broadcaster

### When Viewing Works:
1. Remote video shows broadcaster's feed
2. "Watching Stream X" overlay appears
3. Statistics show bytes received increasing
4. Debug status shows active viewer
5. Stream quality indicator shows "Good"

---

## 🛠️ Advanced Testing

### Multi-Viewer Test:
1. Open multiple browser tabs/windows
2. Create one broadcaster in first tab
3. Connect multiple viewers from other tabs
4. Check debug status for multiple viewers

### Quality Testing:
1. Test different video qualities (360p to 1080p)
2. Monitor bandwidth usage in statistics
3. Check connection stability over time

### Error Recovery:
1. Disconnect network briefly
2. Check if connection recovers automatically
3. Test stopping and restarting streams

---

## 📊 Monitoring Tools

### Real-time Statistics:
- **Broadcaster:** Bytes sent, packets lost, uptime
- **Viewer:** Bytes received, packets lost, quality
- **System:** Active connections, broadcaster count

### Logging:
- All WebRTC events are logged with timestamps
- Export logs for detailed analysis
- Color-coded log levels (info, success, warning, error)

---

## 🎉 Success Criteria

✅ **Streaming is working when:**
1. Local video shows live camera feed
2. Remote video shows broadcaster's feed
3. Both sides show "connected" status
4. Statistics show data flowing
5. Stream list shows "LIVE" status
6. Debug status shows active connections

If all these criteria are met, your WebRTC implementation is working correctly!
