public class GenOffByOneFix011 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int[] duplicate(int[] prices) {
        int[] copy = new int[prices.length];
        for (int i = 0; i < prices.length; i++) {
            copy[i] = prices[i];
        }
        return copy;
    }
}
