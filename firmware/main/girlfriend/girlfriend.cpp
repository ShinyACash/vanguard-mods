#include "girlfriend.h"
#include "../ui/renderer.h"
#include "../ui/widgets.h"
#include "../ui/theme.h"
#include "../display/display.h"
#include "../input/input.h"
#include "../leds/led_manager.h"
#include "../leds/led_chain.h"
#include "../audio/audio_manager.h"
#include "../../include/config.h"

#include <Arduino.h>
#include <NimBLEDevice.h>
#include "miku_data.h"
#include <string>

namespace girlfriend {

static const char* SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b";
static const char* CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8";

static NimBLEServer* s_server = nullptr;
static NimBLECharacteristic* s_char = nullptr;
static NimBLEAdvertising* s_adv = nullptr;

static std::string s_message = "Waiting for PC...";
static int s_mood = 0;
static bool s_dirty = true;
static bool s_bleInit = false;

// High-pitched, fast synthetic chirps to mimic Miku's vocaloid voice
static const audio::Note kVoiceNotes[] = {
    { 2800, 40 }, { 3136, 40 }, { 3520, 40 }, { 0, 20 },
    { 3136, 40 }, { 3520, 40 }, { 4186, 60 }, { 3951, 80 },
    { 4186, 100 }
};

class GFCallbacks : public NimBLECharacteristicCallbacks {
    void onWrite(NimBLECharacteristic* pChar, NimBLEConnInfo& connInfo) override {
        std::string val = pChar->getValue();
        if (val.length() > 0) {
            // Expecting format: "M<mood_0_to_14>:<message>"
            if (val[0] == 'M') {
                size_t colonPos = val.find(':');
                if (colonPos != std::string::npos) {
                    s_mood = atoi(val.substr(1, colonPos - 1).c_str());
                    if (s_mood < 0) s_mood = 0;
                    if (s_mood > 14) s_mood = 14;
                    s_message = val.substr(colonPos + 1);
                } else {
                    s_message = val;
                }
            } else {
                s_message = val;
            }
            s_dirty = true;
            audio::playSfx(kVoiceNotes, 4);
        }
    }
};

void enter() {
    s_dirty = true;
    s_message = "Waiting for PC...";
    s_mood = 0;
    
    // Suppress the baseline LED challenge indicator so we have full control over LEDs
    led::setBaselineSuppressed(true);
    led::stop(); // stop any other playing effects
    
    if (!s_bleInit) {
        NimBLEDevice::init("Vanguard-GF");
        s_server = NimBLEDevice::createServer();
        NimBLEService* pService = s_server->createService(SERVICE_UUID);
        s_char = pService->createCharacteristic(
            CHAR_UUID,
            NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR
        );
        s_char->setCallbacks(new GFCallbacks());
        // pService->start(); (deprecated)
        s_adv = NimBLEDevice::getAdvertising();
        s_adv->addServiceUUID(SERVICE_UUID);
        s_adv->start();
        s_bleInit = true;
    } else {
        if (s_adv) s_adv->start();
    }
}

AppState frame() {
    if (input::wasPressed(input::Button::Back)) {
        if (s_adv) s_adv->stop();
        leds::clearAll();
        return AppState::MainMenu;
    }
    
    if (s_dirty) {
        auto& tft = display::tft();
        ui::widgets::clearScreen(tft);
        
        // Draw Header
        ui::widgets::header(tft, ui::Rect{0, 0, (int16_t)cfg::DISPLAY_WIDTH, (int16_t)theme::LIST_START_Y}, "Girlfriend");
        
        tft.drawRGBBitmap((cfg::DISPLAY_WIDTH - MIKU_WIDTH) / 2, 35, MIKU_BITMAP, MIKU_WIDTH, MIKU_HEIGHT);
        
        // Draw Message
        tft.setTextColor(theme::COLOR_TEXT);
        tft.setTextSize(2);
        tft.setCursor(10, 140);
        // Word wrap naive approach or just rely on ST7789 built-in text wrap
        tft.setTextWrap(true);
        tft.print(s_message.c_str());
        
        s_dirty = false;
    }
    
    // Update LEDs for Love Meter
    // Since led_manager::update() ran before this, it might have cleared the chain.
    // We rewrite the chain state every frame.
    for (int i = 1; i <= 14; i++) {
        leds::setChainLed(i, i <= s_mood);
    }
    
    return AppState::Girlfriend;
}

} // namespace girlfriend
