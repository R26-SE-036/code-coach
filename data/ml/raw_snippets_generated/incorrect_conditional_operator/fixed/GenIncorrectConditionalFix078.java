public class GenIncorrectConditionalFix078 {
    static boolean matches(boolean loaded, boolean ready) {
        if (loaded == ready) {
            return true;
        }
        return false;
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
