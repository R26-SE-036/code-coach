public class GenCleanScannerLoop017 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe2(int attempts) {
        if (attempts < 5) {
            return "low";
        } else if (attempts > 20) {
            return "high";
        }
        return "medium";
    }

    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }
}
