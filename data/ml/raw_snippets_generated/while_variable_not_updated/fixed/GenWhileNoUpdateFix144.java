public class GenWhileNoUpdateFix144 {
    static int drain1(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void countdown(int attempts) {
        while (attempts > 0) {
            System.out.println("left: " + attempts);
            attempts--;
        }
    }
}
