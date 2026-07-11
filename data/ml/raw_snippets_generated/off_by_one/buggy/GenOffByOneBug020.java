public class GenOffByOneBug020 {
    static int[] duplicate(int[] values) {
        int[] copy = new int[values.length];
        for (int i = 0; i <= values.length; i++) {
            copy[i] = values[i];
        }
        return copy;
    }

    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static boolean isEven2(int points) {
        return points % 2 == 0;
    }

    static int sum3(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
