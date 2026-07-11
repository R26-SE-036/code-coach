public class GenWhileNoUpdateFix150 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int attempts) {
        if (attempts < 100) {
            return "low";
        } else if (attempts > 500) {
            return "high";
        }
        return "medium";
    }

    static String describe3(int points) {
        if (points < 5) {
            return "low";
        } else if (points > 20) {
            return "high";
        }
        return "medium";
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

    static int sum5(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static void countdown(int stock) {
        while (stock > 0) {
            System.out.println("left: " + stock);
            stock--;
        }
    }
}
