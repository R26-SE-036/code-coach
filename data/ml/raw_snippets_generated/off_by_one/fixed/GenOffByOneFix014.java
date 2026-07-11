public class GenOffByOneFix014 {
    static int drain1(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static int addUp(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
