public class GenIncorrectConditionalFix124 {
    static void announce(int count) {
        if (count == 10) {
            System.out.println("hit the target");
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
}
