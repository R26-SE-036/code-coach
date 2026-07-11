public class GenWhileNoUpdateFix059 {
    static void pump(boolean open, int attempts) {
        while (!open) {
            System.out.println(attempts);
            attempts++;
            open = attempts > 10;
        }
    }

    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll2(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int drain3(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static int largest4(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static String describe5(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
    }
}
