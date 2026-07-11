public class GenIncorrectConditionalBug128 {
    static boolean matches(boolean enabled, boolean valid) {
        if (enabled = valid) {
            return true;
        }
        return false;
    }

    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int sum2(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static String describe3(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
    }

    static String describe4(int stock) {
        if (stock < 5) {
            return "low";
        } else if (stock > 20) {
            return "high";
        }
        return "medium";
    }
}
