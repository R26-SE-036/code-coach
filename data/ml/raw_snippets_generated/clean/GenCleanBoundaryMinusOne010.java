public class GenCleanBoundaryMinusOne010 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static int sum3(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static int drain4(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static int tally(int[] values) {
        int total = 0;
        for (int i = 0; i <= values.length - 1; i++) {
            total += values[i];
        }
        return total;
    }

    static boolean isEven5(int count) {
        return count % 2 == 0;
    }
}
