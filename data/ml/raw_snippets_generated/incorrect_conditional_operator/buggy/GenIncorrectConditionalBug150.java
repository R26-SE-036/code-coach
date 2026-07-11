public class GenIncorrectConditionalBug150 {
    static String report(boolean active) {
        if (active = true) {
            return "draft";
        }
        return "closed";
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
