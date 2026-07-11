public class GenCleanScannerLoop019 {
    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }

    static String describe1(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven2(int quota) {
        return quota % 2 == 0;
    }
}
