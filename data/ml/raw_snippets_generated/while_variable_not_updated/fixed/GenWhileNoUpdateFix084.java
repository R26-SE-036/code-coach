public class GenWhileNoUpdateFix084 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int drain2(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static boolean isEven3(int level) {
        return level % 2 == 0;
    }

    static boolean isEven4(int steps) {
        return steps % 2 == 0;
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe6(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static int largest7(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static int average8(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void pump(boolean loaded, int budget) {
        while (!loaded) {
            System.out.println(budget);
            budget++;
            loaded = budget > 10;
        }
    }
}
