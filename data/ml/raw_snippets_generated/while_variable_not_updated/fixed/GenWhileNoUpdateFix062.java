public class GenWhileNoUpdateFix062 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void countdown(int quota) {
        while (quota > 0) {
            System.out.println("left: " + quota);
            quota--;
        }
    }
}
