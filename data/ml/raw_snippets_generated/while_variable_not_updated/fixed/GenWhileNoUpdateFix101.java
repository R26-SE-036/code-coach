public class GenWhileNoUpdateFix101 {
    static int largest1(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int drain3(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static String describe4(int count) {
        if (count < 10) {
            return "low";
        } else if (count > 50) {
            return "high";
        }
        return "medium";
    }

    static void countdown(int stock) {
        while (stock > 0) {
            System.out.println("left: " + stock);
            stock--;
        }
    }

    static int largest5(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }
}
