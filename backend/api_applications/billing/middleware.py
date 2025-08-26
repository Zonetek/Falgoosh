class WebhookSecurityMiddleware:
    """Django middleware for webhook security"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add client IP to request for security checks
        client_ip = self.get_client_ip(request)
        request.webhook_client_ip = client_ip

        # Add security headers to response
        response = self.get_response(request)

        if request.path.startswith("/webhooks/"):
            response["X-Webhook-Security"] = "enabled"
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "DENY"

        return response

    def get_client_ip(self, request):
        """Get real client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip