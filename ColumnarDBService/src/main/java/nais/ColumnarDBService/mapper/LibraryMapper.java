package nais.ColumnarDBService.mapper;

import nais.ColumnarDBService.dto.BookDTO;
import nais.ColumnarDBService.dto.LoanDTO;
import nais.ColumnarDBService.dto.MemberDTO;
import nais.ColumnarDBService.dto.ReturnDTO;
import nais.ColumnarDBService.entity.*;
import org.mapstruct.Mapper;

import org.mapstruct.Mapping;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel= "spring")
public interface LibraryMapper {
    //LibraryMapper mapper = Mappers.getMapper(LibraryMapper.class);
    Member memberDTOToMember(MemberDTO dto);
    MemberDTO memberToMemberDTO(Member member);
    BookByGenre bookDTOToBookByGenre(BookDTO dto);
    BookDTO bookByGenreToBookDTO(BookByGenre book);

    //@Mapping(target = "memberName", ignore = true)
    LoanByMember loanDTOToLoanByMember(LoanDTO dto);
    //@Mapping(target = "memberName", ignore = true)
    LoanDTO loanByMemberToLoanDTO(LoanByMember loan);

    //@Mapping(target = "bookGenre", ignore = true)
    //@Mapping(target = "loanDurationDays", ignore = true)
    LoanByBook loanDTOToLoanByBook(LoanDTO dto);

    LoanDTO loanByBookToLoanDTO(LoanByBook loan);
    ReturnByDate returnDTOToReturnByDate(ReturnDTO dto);
    ReturnDTO returnByDateToReturnDTO(ReturnByDate returnByDate);

}
