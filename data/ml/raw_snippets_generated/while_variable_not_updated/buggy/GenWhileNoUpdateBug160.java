public class GenWhileNoUpdateBug160 {
    static int drain1(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static int gather(int steps, int points) {
        int sum = 0;
        while (steps < points) {
            sum += steps;
        }
        return sum;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
