public class GenCleanBoundaryMinusOne015 {
    static int tally(int[] ratings) {
        int total = 0;
        for (int i = 0; i <= ratings.length - 1; i++) {
            total += ratings[i];
        }
        return total;
    }

    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean isEven2(int total) {
        return total % 2 == 0;
    }

    static int drain3(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }
}
