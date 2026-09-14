# Fixture stub -- see ../../README.md.

def register_routes(app):
    @app.route('/orders/<order_id>')
    def get_order(order_id):
        return {'order_id': order_id}
