public class GenIncorrectConditionalBug017 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void announce(int total) {
        if (total = 5) {
            System.out.println("hit the target");
        }
    }
}
