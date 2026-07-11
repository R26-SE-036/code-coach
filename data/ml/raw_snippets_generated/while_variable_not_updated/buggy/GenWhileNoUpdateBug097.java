public class GenWhileNoUpdateBug097 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void pump(boolean active, int total) {
        while (!active) {
            System.out.println(total);
            total++;
        }
    }
}
