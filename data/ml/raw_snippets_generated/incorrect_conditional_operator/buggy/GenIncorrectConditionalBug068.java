public class GenIncorrectConditionalBug068 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int points) {
        if (points < 100) {
            return "low";
        } else if (points > 500) {
            return "high";
        }
        return "medium";
    }

    static void announce(int budget) {
        if (budget = 5) {
            System.out.println("hit the target");
        }
    }
}
