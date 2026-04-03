from firebase_admin import messaging

def send_notification(token: str, title: str, body: str):
    # Create a message to send to the device
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )

    # Send the message
    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Create a multicast message to send to multiple devices IF NEEDED
#def send_multicast_notification(tokens: list, title: str, body: str):
#
#    message = messaging.MulticastMessage(
#        notification=messaging.Notification(
#            title=title,
#            body=body,
#        ),
#        tokens=tokens,
#    )
#
#    Send the message
#    try:
#        response = messaging.send_multicast(message)
#        print(f"Successfully sent multicast message: {response.success_count} successful, {response.failure_count} failed")
#    except Exception as e:
#        print(f"Error sending multicast message: {e}")