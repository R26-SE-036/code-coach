public class GenWhileNoUpdateFix161 {
    static void printAll1(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void countdown(int points) {
        while (points > 0) {
            System.out.println("left: " + points);
            points--;
        }
    }

    static int drain3(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static int largest4(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }

    static String describe5(int level) {
        if (level < 10) {
            return "low";
        } else if (level > 50) {
            return "high";
        }
        return "medium";
    }
}
