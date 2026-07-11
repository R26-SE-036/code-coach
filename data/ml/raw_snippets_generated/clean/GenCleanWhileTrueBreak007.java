public class GenCleanWhileTrueBreak007 {
    static int spin(int budget) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > budget) {
                break;
            }
        }
        return rounds;
    }
}
