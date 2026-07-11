public class GenCleanGeneric083 {
    static int drain1(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static boolean isEven2(int quota) {
        return quota % 2 == 0;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe4(int stock) {
        if (stock < 100) {
            return "low";
        } else if (stock > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven5(int steps) {
        return steps % 2 == 0;
    }

    static int sum6(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static int drain7(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }
}
