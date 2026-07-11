public class GenOffByOneBug060 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void show(int[] values) {
        for (int i = 0; i <= values.length; i++) {
            System.out.println(values[i]);
        }
    }
}
