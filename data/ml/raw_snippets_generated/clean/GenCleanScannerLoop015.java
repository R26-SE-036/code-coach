public class GenCleanScannerLoop015 {
    static int sum1(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static int drain2(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }
}
