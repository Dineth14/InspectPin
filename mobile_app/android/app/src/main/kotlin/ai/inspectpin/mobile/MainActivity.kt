package ai.inspectpin.mobile

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.app.Activity
import android.content.Intent

class MainActivity : FlutterActivity() {
    private var reply: MethodChannel.Result? = null
    private var evidence: ByteArray? = null
    private var player: android.media.MediaPlayer? = null
    private var videoDialog: android.app.AlertDialog? = null
    private fun stopPlayback() {
        player?.release()
        player = null
    }
    override fun onStop() {
        videoDialog?.dismiss()
        stopPlayback()
        super.onStop()
    }

    override fun configureFlutterEngine(engine: FlutterEngine) {
        super.configureFlutterEngine(engine)
        MethodChannel(engine.dartExecutor.binaryMessenger, "ai.inspectpin.mobile/evidence")
            .setMethodCallHandler { call, result ->
                if (call.method == "stop") { stopPlayback(); result.success(null); return@setMethodCallHandler }
                if (call.method == "video") {
                    var file: java.io.File? = null
                    try {
                        videoDialog?.dismiss()
                        stopPlayback()
                        val clip = java.io.File.createTempFile("inspectpin-", ".mp4", cacheDir)
                        file = clip
                        clip.writeBytes(call.arguments as ByteArray)
                        val view = android.widget.VideoView(this)
                        val controls = android.widget.MediaController(this)
                        controls.setAnchorView(view)
                        view.setMediaController(controls)
                        val dialog = android.app.AlertDialog.Builder(this)
                            .setTitle("Silent video").setView(view).setPositiveButton("Close", null).create()
                        dialog.setOnDismissListener {
                            view.stopPlayback()
                            clip.delete()
                            videoDialog = null
                        }
                        videoDialog = dialog
                        dialog.show()
                        view.setVideoPath(clip.absolutePath)
                        view.start()
                        result.success(null)
                    } catch (e: Exception) {
                        videoDialog?.dismiss()
                        file?.delete()
                        result.error("PLAY_FAILED", "Could not open silent video", null)
                    }
                    return@setMethodCallHandler
                }
                if (call.method == "play") {
                    stopPlayback()
                    try {
                        val audio = java.io.File.createTempFile("inspectpin-", ".wav", cacheDir)
                        try {
                            audio.writeBytes(call.arguments as ByteArray)
                            player = android.media.MediaPlayer()
                            java.io.FileInputStream(audio).use { player!!.setDataSource(it.fd) }
                            player!!.prepare()
                            player!!.setOnCompletionListener { stopPlayback() }
                            player!!.start()
                        } finally { audio.delete() }
                        result.success(null)
                    } catch (e: Exception) {
                        stopPlayback(); result.error("PLAY_FAILED", "Audio playback failed", null)
                    }
                    return@setMethodCallHandler
                }
                if (call.method != "save") { result.notImplemented(); return@setMethodCallHandler }
                if (reply != null) { result.error("BUSY", "Finish the current export", null); return@setMethodCallHandler }
                evidence = call.argument<ByteArray>("bytes")
                reply = result
                try {
                    startActivityForResult(Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = call.argument<String>("mime")
                        putExtra(Intent.EXTRA_TITLE, call.argument<String>("name"))
                    }, 9271)
                } catch (e: Exception) {
                    evidence = null; reply = null
                    result.error("EXPORT_FAILED", "Document picker unavailable", null)
                }
            }
    }

    @Deprecated("Used by the platform document picker")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != 9271) return
        val callback = reply ?: return
        val bytes = evidence
        reply = null; evidence = null
        val uri = data?.data
        if (resultCode != Activity.RESULT_OK || uri == null || bytes == null) {
            callback.error("CANCELLED", "Export cancelled", null); return
        }
        Thread {
            try {
                requireNotNull(contentResolver.openOutputStream(uri)).use { it.write(bytes) }
                runOnUiThread { callback.success(null) }
            } catch (e: Exception) {
                runOnUiThread { callback.error("EXPORT_FAILED", "Could not save evidence", null) }
            }
        }.start()
    }
}
