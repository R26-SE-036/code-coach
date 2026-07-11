public class GenCleanGeneric088 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe2(int quota) {
        if (quota < 10) {
            return "low";
        } else if (quota > 50) {
            return "high";
        }
        return "medium";
    }

    static int drain3(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }
}
