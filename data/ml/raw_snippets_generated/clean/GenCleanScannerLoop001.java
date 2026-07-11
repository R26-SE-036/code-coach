public class GenCleanScannerLoop001 {
    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }

    static boolean isEven1(int quota) {
        return quota % 2 == 0;
    }
}
