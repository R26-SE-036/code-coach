public class GenCleanGeneric112 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll2(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }
}
