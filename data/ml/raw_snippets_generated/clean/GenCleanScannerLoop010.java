public class GenCleanScannerLoop010 {
    static void printAll1(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }
}
