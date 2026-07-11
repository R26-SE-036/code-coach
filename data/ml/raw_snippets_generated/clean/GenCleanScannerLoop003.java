public class GenCleanScannerLoop003 {
    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static void printAll2(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }
}
