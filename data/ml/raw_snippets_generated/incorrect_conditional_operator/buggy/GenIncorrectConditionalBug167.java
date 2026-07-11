public class GenIncorrectConditionalBug167 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String report(boolean done) {
        if (done = true) {
            return "active";
        }
        return "expired";
    }
}
