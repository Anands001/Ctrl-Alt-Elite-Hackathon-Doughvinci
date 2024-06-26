from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


class Order:
    def __init__(self, order_id, kitchen_id, customer_id, pickup_time, location):
        self.order_id = order_id
        self.kitchen_id = kitchen_id
        self.customer_id = customer_id
        self.pickup_time = pickup_time
        self.location = location


class Rider:
    def __init__(self, rider_id, current_location):
        self.rider_id = rider_id
        self.current_location = current_location


class DeliveryBatch:
    def __init__(self):
        self.orders = []
        self.destination = None


def calculate_distance(location1, location2):
    # Calculate Manhattan distance between two locations
    x1, y1 = location1
    x2, y2 = location2
    return abs(x2 - x1) + abs(y2 - y1)


def group_orders(orders):
    grouped_orders = []

    def group_orders_by_rule(order_key_func):
        order_groups = {}
        for order in orders:
            key = order_key_func(order)
            if key in order_groups:
                order_groups[key].append(order)
            else:
                order_groups[key] = [order]
        for orders_list in order_groups.values():
            if len(orders_list) > 1:
                sorted_orders = sorted(orders_list, key=lambda x: datetime.strptime(x.pickup_time, '%I:%M %p'))
                group = [sorted_orders[0]]
                for i in range(1, len(sorted_orders)):
                    prev_time = datetime.strptime(sorted_orders[i - 1].pickup_time, '%I:%M %p')
                    current_time = datetime.strptime(sorted_orders[i].pickup_time, '%I:%M %p')
                    time_difference = (current_time - prev_time).total_seconds() / 60  # Convert to minutes
                    if time_difference <= 10:
                        group.append(sorted_orders[i])
                    else:
                        grouped_orders.append(group)
                        group = [sorted_orders[i]]
                grouped_orders.append(group)

    # Rule #1: Group orders from the same kitchen and customer with similar ready times
    group_orders_by_rule(lambda order: (order.kitchen_id, order.customer_id))

    # Rule #2: Group orders from two different kitchens to the same customer
    group_orders_by_rule(lambda order: order.customer_id)

    # Rule #3: Group orders from the same kitchen to two different customers
    group_orders_by_rule(lambda order: order.kitchen_id)

    # Rule #4: Group orders to the same customer with 2nd kitchen pickup on the way
    customer_kitchen_pickup = {}
    for order in orders:
        key = (order.customer_id, order.kitchen_id)
        if key in customer_kitchen_pickup:
            customer_kitchen_pickup[key].append(order)
        else:
            customer_kitchen_pickup[key] = [order]
    for _, orders in customer_kitchen_pickup.items():
        if len(orders) == 2:
            # Check if the pickup times are 10 minutes apart
            pickup_times = [datetime.strptime(order.pickup_time, '%I:%M %p') for order in orders]
            time_diff = (pickup_times[1] - pickup_times[0]).total_seconds() / 60
            if time_diff == 10:
                grouped_orders.append(orders)

    # Rule #5: Group orders with 2nd customer drop on the way to the 1st customer
    for order1 in orders:
        for order2 in orders:
            if order1.customer_id != order2.customer_id:
                # Check if the pickup times are 10 minutes apar t or if the pickup time is before reaching the kitchen
                pickup_time1 = datetime.strptime(order1.pickup_time, '%I:%M %p')
                pickup_time2 = datetime.strptime(order2.pickup_time, '%I:%M %p')
                time_diff = (pickup_time2 - pickup_time1).total_seconds() / 60
                if time_diff == 10 or pickup_time2 <= pickup_time1:
                    grouped_orders.append([order1, order2])

    return grouped_orders


def optimize_route(delivery_batch):
    orders = delivery_batch.orders
    if not orders:
        return

    # Calculate the centroid of the orders' locations as the destination
    centroid_x = sum(order.location[0] for order in orders) / len(orders)
    centroid_y = sum(order.location[1] for order in orders) / len(orders)
    delivery_batch.destination = (centroid_x, centroid_y)


def assign_batches_to_riders(delivery_batches, riders):
    assigned_orders = set()  # Track assigned orders
    assigned_batches = {rider.rider_id: [] for rider in riders}

    # Sort the riders by their current location
    riders.sort(key=lambda rider: rider.current_location)

    # Assign batches to riders based on their availability and distance
    for batch in delivery_batches:
        closest_rider = None
        min_distance = float('inf')

        # Find the closest available rider to the batch destination
        for rider in riders:
            if batch.destination not in assigned_orders:  # Check if the batch destination has been assigned
                distance_to_batch = calculate_distance(rider.current_location, batch.destination)
                if distance_to_batch < min_distance:
                    min_distance = distance_to_batch
                    closest_rider = rider

        if closest_rider:
            assigned_batches[closest_rider.rider_id].append(batch)
            assigned_orders.add(batch.destination)  # Mark the destination as assigned

    return assigned_batches


# Generate random orders
def generate_orders(num_orders):
    orders = []
    for i in range(1, num_orders + 1):
        order_id = i
        kitchen_id = f'kitchen{random.randint(1, 5)}'  # Corrected usage of random.randint
        customer_id = f'customer{random.randint(1, 20)}'
        pickup_time = (datetime.now() + timedelta(minutes=random.randint(0, 120))).strftime('%I:%M %p')
        location = (random.uniform(0, 10), random.uniform(0, 10))  # Random location
        orders.append(Order(order_id, kitchen_id, customer_id, pickup_time, location))
    return orders


# Generate random riders
def generate_riders(num_riders):
    riders = []
    for i in range(1, num_riders + 1):
        rider_id = i
        current_location = (random.uniform(0, 10), random.uniform(0, 10))  # Random location
        riders.append(Rider(rider_id, current_location))
    return riders


# Generate a sample dataset
def generate_dataset(num_orders, num_riders):
    orders = generate_orders(num_orders)
    riders = generate_riders(num_riders)
    return orders, riders




def plot_orders_and_batches(orders, assigned_batches, riders):
    plt.figure(figsize=(10, 8))

    # Plot orders
    for order in orders:
        plt.scatter(order.location[0], order.location[1], color='blue', alpha=0.5)

    # Plot delivery batches and connect them to rider's current location
    for rider in riders:  # Iterate over riders directly, since riders is a list
        rider_location = rider.current_location
        rider_id = rider.rider_id  # Access rider ID if needed
        if rider_id in assigned_batches:
            batches = assigned_batches[rider_id]
            for batch in batches:
                batch_destination = batch.destination
                plt.scatter(batch_destination[0], batch_destination[1], color='green', marker='s')
                plt.plot([rider_location[0], batch_destination[0]], [rider_location[1], batch_destination[1]],
                         color='orange', linestyle='-', linewidth=2, alpha=0.5)
                for order in batch.orders:
                    plt.plot([order.location[0], batch_destination[0]], [order.location[1], batch_destination[1]],
                             color='gray', linestyle='--', alpha=0.5)

    # Plot rider's current location
    for rider in riders:
        plt.scatter(rider.current_location[0], rider.current_location[1], color='red', marker='^')

    # Create custom patches for the legend
    orders_patch = mpatches.Patch(color='blue', label='Orders')
    batch_destination_patch = mpatches.Patch(color='green', label='Batch Destination')
    rider_location_patch = mpatches.Patch(color='red', label='Rider Location')

    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Orders, Riders, and Delivery Batches')
    plt.legend(handles=[orders_patch, batch_destination_patch, rider_location_patch])
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    # Generate a dataset with 20 orders and 5 riders
    orders, riders = generate_dataset(20, 5)

    # Step 1: Group orders based on rules
    grouped_orders = group_orders(orders)

    # Step 2: Optimize route for each delivery batch
    delivery_batches = []
    for group in grouped_orders:
        delivery_batch = DeliveryBatch()
        delivery_batch.orders = group
        optimize_route(delivery_batch)
        delivery_batches.append(delivery_batch)

    # Step 3: Assign delivery batches to riders
    assigned_batches = assign_batches_to_riders(delivery_batches, riders)

    # Print the assigned batches in a more understandable format
    print("Assigned Batches to Riders:")
    for rider_id, batches in assigned_batches.items():
        print(f"Rider ID: {rider_id}")
        if (rider_id < len(riders)):
            print(f"Current Location: {riders[rider_id].current_location}")
        for batch in batches:
            print(f"Batch Destination: {batch.destination}")
            print("Orders in the Batch:")
            for order in batch.orders:
                print(
                    f"- Order ID: {order.order_id}, Kitchen ID: {order.kitchen_id}, Customer ID: {order.customer_id}, Pickup Time: {order.pickup_time}, Location: {order.location}")
            print()
    plot_orders_and_batches(orders, assigned_batches, riders)
