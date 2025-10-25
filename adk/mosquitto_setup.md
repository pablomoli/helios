# MQTT Broker Setup - Connecting Raspberry Pi and Laptop

## On Raspberry Pi (MQTT Broker)

### 1. Find Raspberry Pi's IP Address
```bash
hostname -I
# Example output: 192.168.1.100 (use the first IP address)
```

### 2. Configure Mosquitto to Accept Remote Connections
Create/edit the Mosquitto config file:
```bash
sudo nano /etc/mosquitto/conf.d/helios.conf
```

Add these lines:
```
listener 1883
allow_anonymous true
```

**Note:** For production, you should use authentication. For development/testing, `allow_anonymous` is fine.

### 3. Restart Mosquitto
```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

You should see: `Active: active (running)`

### 4. Test Local Connection
```bash
# Subscribe to test topic
mosquitto_sub -h localhost -t test/topic

# In another terminal, publish a message
mosquitto_pub -h localhost -t test/topic -m "Hello from Pi"
```

### 5. Check Firewall (if applicable)
```bash
# Allow MQTT port through firewall
sudo ufw allow 1883
```

---

## On Your Laptop (MQTT Client)

### 1. Get Raspberry Pi's IP
Use the IP you got from Step 1 on the Pi (e.g., `192.168.1.100`)

### 2. Test Connection from Laptop
```bash
# Test if you can reach the Pi's broker
mosquitto_sub -h 192.168.1.100 -t test/topic

# In another terminal, publish from your laptop
mosquitto_pub -h 192.168.1.100 -t test/topic -m "Hello from laptop"
```

If you see the message, the connection works! 🎉

### 3. Configure Helios Services

#### For Dashboard:
Edit `/home/leo/code/helios/dashboard/dashboard.py` or create a `.env` file:
```bash
MQTT_BROKER_HOST=192.168.1.100
MQTT_BROKER_PORT=1883
```

#### For ADK Agent:
Edit `/home/leo/code/helios/adk/helios_agent/.env`:
```
MQTT_BROKER_HOST=192.168.1.100
MQTT_BROKER_PORT=1883
```

---

## Quick Connection Test

### Terminal 1 (Raspberry Pi):
```bash
mosquitto_sub -h localhost -t helios/test
```

### Terminal 2 (Your Laptop):
```bash
mosquitto_pub -h 192.168.1.100 -t helios/test -m "Laptop connected!"
```

You should see "Laptop connected!" appear on the Pi.

### Terminal 3 (Your Laptop - reverse test):
```bash
mosquitto_sub -h 192.168.1.100 -t helios/test
```

### Terminal 4 (Raspberry Pi):
```bash
mosquitto_pub -h localhost -t helios/test -m "Pi says hello!"
```

---

## Troubleshooting

### Can't connect from laptop to Pi?

1. **Check both devices are on same WiFi network:**
   ```bash
   # On Pi
   ip addr show wlan0

   # On laptop
   ip addr
   ```

2. **Ping the Pi from laptop:**
   ```bash
   ping 192.168.1.100
   ```

3. **Check Mosquitto is listening on all interfaces:**
   ```bash
   # On Pi
   sudo netstat -tulpn | grep 1883
   ```
   Should show: `0.0.0.0:1883` (not `127.0.0.1:1883`)

4. **Check Mosquitto logs:**
   ```bash
   # On Pi
   sudo journalctl -u mosquitto -f
   ```

5. **Firewall blocking?**
   ```bash
   # On Pi (if using ufw)
   sudo ufw status
   sudo ufw allow 1883
   ```

### Connection works but no data?

- Make sure services are publishing to the correct topics
- Check topic names match exactly (case-sensitive)
- Use `mosquitto_sub -h 192.168.1.100 -t '#'` to see ALL topics

---

## Expected Topic Structure

Once connected, you should see these topics:

**From Pi (sensors/hardware):**
- `helios/sensors/raw`
- `helios/status`

**From Laptop (commands):**
- `helios/command/position`
- `helios/command/mode`

**From Laptop (AI/analytics):**
- `helios/ai/performance_delta`
- `helios/impact`
- `helios/safety`

---

## Production Setup (Optional)

For better security, configure authentication:

```bash
# On Pi
sudo mosquitto_passwd -c /etc/mosquitto/passwd helios_user

# Edit /etc/mosquitto/conf.d/helios.conf
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd

# Restart
sudo systemctl restart mosquitto
```

Then update all clients to use username/password:
```bash
mosquitto_pub -h 192.168.1.100 -u helios_user -P your_password -t test/topic -m "test"
```
