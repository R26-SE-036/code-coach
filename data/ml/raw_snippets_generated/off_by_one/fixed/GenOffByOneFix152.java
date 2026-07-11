public class GenOffByOneFix152 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int sum2(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static int addUp(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static int drain3(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static String describe4(int steps) {
        if (steps < 100) {
            return "low";
        } else if (steps > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven5(int quota) {
        return quota % 2 == 0;
    }

    static boolean isEven6(int budget) {
        return budget % 2 == 0;
    }

    static int largest7(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }
}
